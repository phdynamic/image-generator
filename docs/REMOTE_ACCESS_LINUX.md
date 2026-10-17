# Running Imaginaree on Linux and reaching it from anywhere

This sets Imaginaree up on a Linux machine with an NVIDIA GPU (written for
Bazzite) so it runs in the background, and you open it in a browser at your own
domain from any device. Images are generated on that machine's GPU.

How it fits together:

```
any browser ──https──▶ Cloudflare ──tunnel──▶ your machine ─▶ Imaginaree (password) ─▶ GPU
```

Nothing is opened on your router. The machine makes an outbound connection to
Cloudflare, and Imaginaree asks for a password before showing anything.

## 1. Install Imaginaree on the machine

```bash
git clone https://github.com/phdynamic/image-generator.git ~/imaginaree
cd ~/imaginaree
git checkout claude/plan-image-generator-app-6cYP8
bash scripts/setup_linux.sh
```

The script:

- creates a Python environment in `backend/venv` (nothing is layered onto the
  immutable system)
- installs the packages, including the CUDA build of PyTorch (several GB)
- checks that PyTorch can see your GPU, and warns if it can't
- asks you to choose a **password** (use a long passphrase)
- installs and starts a background service that also starts at boot

When it finishes, open <http://127.0.0.1:8000> on that machine and sign in.
Generate one image to confirm the GPU works. The header shows your GPU and how
much VRAM is free. If it says **No GPU (CPU mode)**, generation is running on
the CPU and will be very slow, so see Troubleshooting.

## 2. Create the Cloudflare tunnel

You need your domain on Cloudflare (its nameservers pointed at Cloudflare).
Cloudflare's menus move around from time to time, so use the names below as a
guide.

1. In the Cloudflare dashboard open **Zero Trust**. Cloudflare may ask you to
   pick the free plan and add a payment method first; the free plan isn't charged.
2. Go to **Networks → Tunnels → Create a tunnel**, choose **Cloudflared**, and
   name it `imaginaree`.
3. On the install page pick **Linux** and copy the **token**. It's the long
   string after `--token` (or `service install`) in the command shown. Treat it
   like a password.
4. Open the tunnel's **Public Hostname** tab and add a hostname:
   - Subdomain and domain: for example `images` + `yourdomain.com`
   - Service type: **HTTP**
   - URL: `localhost:8000`

Then, on the machine:

```bash
bash scripts/setup_tunnel.sh
```

Paste the token when asked (it isn't shown as you type). Open
`https://images.yourdomain.com` from any device and sign in.

## 3. Strongly recommended: put Cloudflare Access in front

Imaginaree's password is the only thing between the internet and your GPU. Cloudflare Access
adds a second gate that rejects strangers before they even see the sign-in page.

In **Zero Trust → Access → Applications → Add an application → Self-hosted**:
use your hostname, add a policy that **allows only your email address**, and
choose **One-time PIN** as the login method. You'll get a code by email when you
visit the site from a new browser.

## Everyday use

| Task | Command |
|---|---|
| See what the app is doing | `journalctl --user -u imaginaree -f` |
| Restart the app | `systemctl --user restart imaginaree` |
| Stop / start | `systemctl --user stop imaginaree` / `start` |
| Update to the latest code | `cd ~/imaginaree && git pull && bash scripts/setup_linux.sh` |
| Change the password | `~/imaginaree/backend/venv/bin/python ~/imaginaree/scripts/set_password.py` then restart |
| Check the tunnel | `systemctl --user status cloudflared-imaginaree` |

Changing the password signs everyone out.

## Models

Pick a model from the dropdown. The first use of each one downloads it.

| Model | Download | Notes |
|---|---|---|
| DreamShaper 8 | ~2 GB | Fast drafts and illustrations |
| Juggernaut XL v9 | ~7 GB | Detailed, photorealistic SDXL |
| RealVisXL V5.0 | ~7 GB | Natural, realistic SDXL |
| Segmind SSD-1B | ~5 GB | Lighter SDXL |
| SDXL Turbo | ~6 GB | Drafts in 1-4 steps |
| FLUX.1 schnell | ~34 GB | **Experimental.** Best prompt following and text in images |

Choosing a model sets its recommended steps, guidance and image size. Turbo and
FLUX ignore the guidance slider and negative prompts, so those controls are
locked for them.

**Your 8 GB card is shared with the desktop.** Plasma, Steam and your browser
take roughly 2 GB, so about 6 GB is free for generation. Imaginaree checks the
free VRAM when it loads a model and moves parts of the model to system RAM when
needed, which makes SDXL models slower but lets them fit. For FLUX, close Steam
and other GPU programs first. If you see "ran out of memory", use a smaller image
size or a lighter model.

**Models that need a HuggingFace token:** none of the current ones do. If you
add a gated model later, create a free token at huggingface.co/settings/tokens and
put `HF_TOKEN=...` in `~/imaginaree/.env`.

**Moving things over from another machine:** copy the `models_cache` folder to
skip re-downloading models. To bring your gallery, copy `imaginaree.db` and the
`outputs` folder into `~/imaginaree` while the app is stopped.

## Troubleshooting

- **"No GPU (CPU mode)" in the header.** Run `nvidia-smi`. If that works, PyTorch
  was installed without CUDA. Reinstall it with
  `TORCH_INDEX_URL=https://download.pytorch.org/whl/cu128 bash scripts/setup_linux.sh`.
- **The app won't start.** Run `journalctl --user -u imaginaree -n 50 --no-pager`.
  The most common cause is a missing password: the app refuses to start in public
  mode without one. Run `set_password.py`.
- **The site shows a Cloudflare error.** Check that the app is running
  (`curl http://127.0.0.1:8000/api/auth/status`) and that the tunnel service is
  active.
- **It stops working when you log out or reboot.** The setup script turns on
  "lingering" so the services run without a login. Check with
  `loginctl show-user $USER | grep Linger` (it should say `Linger=yes`).
- **FLUX fails with a bitsandbytes error.** Run
  `~/imaginaree/backend/venv/bin/pip install -r ~/imaginaree/backend/requirements-flux.txt`.

## Good to know

- Keep `APP_HOST=127.0.0.1` in `.env`. The tunnel reaches the app locally, so
  nothing else on your network needs access.
- The sign-in locks an address out for 15 minutes after 5 wrong passwords.
- The **Stash** button sends to a Stashly app on the same device as your browser,
  so it won't reach Stashly when you're using the site remotely.
- Images are generated one at a time. If you queue several, they wait in line.
